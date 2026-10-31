#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Verification Test Suite for Mind Link & MindUI Pairing
==================================================================
Tests:
  1. Config management (atomic JSON save, load, feature toggles)
  2. UDP discovery broadcast, device reception, and probe responses
  3. Dynamic port fallback when ports are occupied
  4. TCP pairing handshake & PIN challenge verification (success & error cases)
  5. Bidirectional live network Universal Clipboard synchronization
  6. GTK4 / Libadwaita Mind Arc UI components & Sidebar registration
  7. CLI execution and flags for both mind-link-service and mindui_pair_agent
"""

import os
import sys
import time
import json
import socket
import unittest
import threading
import subprocess

# Add mind-arc to path
sys.path.insert(0, "/home/mamish/mindos-paradise/src/mind-arc")
sys.path.insert(0, "/home/mamish/Games/mindui-vm/scripts")

import mind_link
from mindui_pair_agent import MindUIPairAgent, get_local_ip


class TestMindLinkConfig(unittest.TestCase):
    def setUp(self):
        self.test_cfg_path = os.path.expanduser("~/.config/mindos/paired_devices.json")

    def test_load_and_save(self):
        cfg = mind_link.MindLinkConfig.load()
        self.assertIn("devices", cfg)
        self.assertIn("settings", cfg)

        test_device = {
            "device_id": "test_unit_01",
            "device_name": "Test MindPhone",
            "device_model": "MindPhone 1",
            "ip": "127.0.0.1",
            "port": 4243,
            "status": "paired",
            "features": {"universal_clipboard": True}
        }
        ok = mind_link.MindLinkConfig.add_device(test_device)
        self.assertTrue(ok)

        # Verify added
        cfg_after = mind_link.MindLinkConfig.load()
        dev_ids = [d["device_id"] for d in cfg_after["devices"]]
        self.assertIn("test_unit_01", dev_ids)

        # Update feature
        mind_link.MindLinkConfig.update_feature("test_unit_01", "universal_clipboard", False)
        cfg_updated = mind_link.MindLinkConfig.load()
        dev = next(d for d in cfg_updated["devices"] if d["device_id"] == "test_unit_01")
        self.assertFalse(dev["features"]["universal_clipboard"])

        # Remove
        mind_link.MindLinkConfig.remove_device("test_unit_01")
        cfg_final = mind_link.MindLinkConfig.load()
        self.assertNotIn("test_unit_01", [d["device_id"] for d in cfg_final["devices"]])


class TestDiscoveryAndHandshake(unittest.TestCase):
    _port_counter = 16000

    def setUp(self):
        TestDiscoveryAndHandshake._port_counter += 4
        self.test_port = TestDiscoveryAndHandshake._port_counter
        self.test_bcast = self.test_port + 1
        self.agent = MindUIPairAgent(
            device_id="test_agent_01",
            device_name="MindUI Phone Unit Test",
            device_model="MindPhone UT",
            ip="127.0.0.1",
            port=self.test_port,
            broadcast_port=self.test_bcast,
            pin="654321",
            auto_confirm=True,
            setup_mode=True,
            one_shot=False
        )
        self.agent_thread = threading.Thread(target=self.agent.start, daemon=True)
        self.agent_thread.start()
        time.sleep(0.3)

    def tearDown(self):
        self.agent.stop()
        time.sleep(0.2)

    def test_tcp_pairing_handshake_success(self):
        dev_info = {
            "device_id": "test_agent_01",
            "device_name": "MindUI Phone Unit Test",
            "device_model": "MindPhone UT",
            "os_version": "MindUI 1.0",
            "ip": "127.0.0.1",
            "port": self.test_port
        }

        pin_received = []
        pair_success_data = []
        error_data = []
        done_event = threading.Event()

        def on_pin_ready(pin, info, decision_cb):
            pin_received.append(pin)
            # User accepts
            decision_cb(True)

        def on_success(res):
            pair_success_data.append(res)
            done_event.set()

        def on_error(err):
            error_data.append(err)
            done_event.set()

        mind_link.MindLinkPairingClient.pair_with_device(
            dev_info,
            on_pin_ready=on_pin_ready,
            on_success=on_success,
            on_error=on_error
        )

        ok = done_event.wait(timeout=5.0)
        self.assertTrue(ok, "Handshake timed out")
        self.assertEqual(len(error_data), 0, f"Unexpected error: {error_data}")
        self.assertEqual(len(pin_received), 1)
        self.assertEqual(pin_received[0], "654321")
        self.assertEqual(len(pair_success_data), 1)
        self.assertEqual(pair_success_data[0]["device_id"], "test_agent_01")
        self.assertEqual(pair_success_data[0]["status"], "connected")

        # Clean up created config entry
        mind_link.MindLinkConfig.remove_device("test_agent_01")

    def test_tcp_pairing_handshake_cancellation(self):
        dev_info = {
            "device_id": "test_agent_01",
            "device_name": "MindUI Phone Unit Test",
            "device_model": "MindPhone UT",
            "os_version": "MindUI 1.0",
            "ip": "127.0.0.1",
            "port": self.test_port
        }

        error_data = []
        done_event = threading.Event()

        def on_pin_ready(pin, info, decision_cb):
            # User cancels
            decision_cb(False)

        def on_success(res):
            done_event.set()

        def on_error(err):
            error_data.append(err)
            done_event.set()

        mind_link.MindLinkPairingClient.pair_with_device(
            dev_info,
            on_pin_ready=on_pin_ready,
            on_success=on_success,
            on_error=on_error
        )

        ok = done_event.wait(timeout=5.0)
        self.assertTrue(ok, "Cancellation timed out")
        self.assertEqual(len(error_data), 1)
        self.assertIn("iptal", error_data[0].lower())

    def test_udp_discovery(self):
        discovered = []
        disc_event = threading.Event()

        def on_found(dev):
            if dev.get("device_id") == "test_agent_01":
                discovered.append(dev)
                disc_event.set()

        discovery = mind_link.MindLinkDiscovery(on_device_found=on_found, port=self.test_bcast)
        discovery.start()
        try:
            ok = disc_event.wait(timeout=6.0)
            self.assertTrue(ok, "UDP discovery did not receive beacon from agent")
            self.assertEqual(discovered[0]["device_name"], "MindUI Phone Unit Test")
        finally:
            discovery.stop()

    def test_probe_discovery_response(self):
        """Verify that MindUI agent responds immediately to mindarc_discover probe."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass
        sock.bind(("0.0.0.0", self.test_bcast))
        sock.settimeout(3.0)

        probe = json.dumps({"type": "mindarc_discover", "timestamp": time.time()}).encode("utf-8")
        sock.sendto(probe, ("127.0.0.1", self.test_bcast))

        received_beacon = False
        start_t = time.time()
        while time.time() - start_t < 3.0:
            try:
                data, _ = sock.recvfrom(2048)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") == "mindui_beacon" and msg.get("device_id") == "test_agent_01":
                    received_beacon = True
                    break
            except socket.timeout:
                break
        sock.close()
        self.assertTrue(received_beacon, "Agent did not reply to mindarc_discover probe")


class TestUniversalClipboard(unittest.TestCase):
    def test_clipboard_read_write(self):
        test_text = f"MindOS Universal Clipboard Test {time.time()}"
        ok = mind_link.ClipboardManager.write_text(test_text)
        self.assertTrue(ok, "Failed to write clipboard text via wl-copy/xclip")
        read_back = mind_link.ClipboardManager.read_text()
        self.assertEqual(read_back, test_text, "Clipboard readback did not match written content")

    def test_network_clipboard_sync_bidirectional(self):
        """
        Tests live network clipboard synchronization between MindLinkServiceDaemon
        and MindUIPairAgent over TCP socket.
        """
        # Import daemon from service script
        import types
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader("mind_link_service", "/home/mamish/mindos-paradise/src/mind-arc/mind-link-service")
        mls = types.ModuleType(loader.name)
        loader.exec_module(mls)

        srv_port = 17500
        agent_port = 17501
        bcast_port = 17502

        # 1. Start simulated phone agent
        agent = MindUIPairAgent(
            device_id="sync_phone_01",
            device_name="Sync Test Phone",
            device_model="MindPhone Sync",
            ip="127.0.0.1",
            port=agent_port,
            broadcast_port=bcast_port,
            pin="112233",
            auto_confirm=True,
            setup_mode=False
        )
        t_agent = threading.Thread(target=agent.start, daemon=True)
        t_agent.start()
        time.sleep(0.3)

        # 2. Register paired device so service connects to it
        paired_entry = {
            "device_id": "sync_phone_01",
            "device_name": "Sync Test Phone",
            "device_model": "MindPhone Sync",
            "ip": "127.0.0.1",
            "port": agent.port,
            "features": {"universal_clipboard": True}
        }
        mind_link.MindLinkConfig.add_device(paired_entry)

        # 3. Start service daemon
        daemon = mls.MindLinkServiceDaemon(port=srv_port, broadcast_port=bcast_port)
        t_daemon = threading.Thread(target=daemon.start, daemon=True)
        t_daemon.start()

        try:
            # Wait for connection establishment
            time.sleep(1.5)

            # Test A: PC broadcasts clipboard -> Phone receives it
            pc_clip = f"Hello from MindOS Paradise PC {time.time()}"
            daemon.broadcast_clipboard(pc_clip)
            time.sleep(0.8)
            self.assertEqual(agent.last_received_clipboard, pc_clip, "Phone did not receive PC clipboard broadcast")

            # Test B: Phone sends clipboard -> Service daemon receives it
            phone_clip = f"Hello from MindUI Phone {time.time()}"
            ok_send = agent.send_clipboard(phone_clip)
            self.assertTrue(ok_send, "Agent failed to send clipboard over session")
            time.sleep(0.8)
            self.assertEqual(daemon.last_remote_clipboard, phone_clip, "Service did not receive phone clipboard update")
        finally:
            daemon.stop()
            agent.stop()
            mind_link.MindLinkConfig.remove_device("sync_phone_01")
            time.sleep(0.2)


class TestDynamicPortFallback(unittest.TestCase):
    def test_port_fallback_when_occupied(self):
        """Verify that MindUIPairAgent binds the next port if the requested port is busy."""
        # Occupy base port
        busy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        busy_sock.bind(("0.0.0.0", 17950))
        busy_sock.listen(1)

        try:
            agent = MindUIPairAgent(
                device_id="fallback_agent",
                device_name="Fallback Phone",
                device_model="MindPhone F",
                ip="127.0.0.1",
                port=17950,
                broadcast_port=17951
            )
            t = threading.Thread(target=agent.start, daemon=True)
            t.start()
            time.sleep(0.4)
            try:
                # Should have fallen back to 17951 or 17952
                self.assertNotEqual(agent.port, 17950)
                self.assertTrue(agent.port > 17950)
            finally:
                agent.stop()
        finally:
            busy_sock.close()


class TestGTKIntegration(unittest.TestCase):
    def test_extra_sidebar_and_page(self):
        import mindarc_extra
        # Verify text mappings
        self.assertIn("mind_link", mindarc_extra.TEXTS)
        tr_title, en_title = mindarc_extra.TEXTS["mind_link"]
        self.assertEqual(tr_title, "MindUI Ekosistem")
        self.assertEqual(en_title, "MindUI Ecosystem")

        # Mock window object
        class MockWin:
            def __init__(self):
                self.current_lang_code = 'tr'

        win = MockWin()
        items = mindarc_extra.extra_sidebar_items(win)
        names = [item[0] for item in items]
        self.assertIn("mind_link", names)
        # Check icon
        ml_item = next(item for item in items if item[0] == "mind_link")
        self.assertEqual(ml_item[1], "📱")
        self.assertEqual(ml_item[2], "MindUI Ekosistem")

        # Test English toggle
        win.current_lang_code = 'en'
        items_en = mindarc_extra.extra_sidebar_items(win)
        ml_item_en = next(item for item in items_en if item[0] == "mind_link")
        self.assertEqual(ml_item_en[2], "MindUI Ecosystem")


class TestServiceCLI(unittest.TestCase):
    def test_service_cli_commands(self):
        # Test status
        res = subprocess.run(["mind-link-service", "--status"], capture_output=True, text=True)
        self.assertNotIn("Traceback", res.stderr)

        # Test rescan
        res_rescan = subprocess.run(["mind-link-service", "--rescan"], capture_output=True, text=True)
        self.assertEqual(res_rescan.returncode, 0)
        self.assertIn("Discovery probe sent", res_rescan.stdout)

    def test_agent_cli_help(self):
        res = subprocess.run([
            sys.executable,
            "/home/mamish/Games/mindui-vm/scripts/mindui_pair_agent.py",
            "--help"
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("MindUI Android Pairing Agent", res.stdout)
        self.assertIn("--clipboard-send", res.stdout)


if __name__ == "__main__":
    unittest.main()
