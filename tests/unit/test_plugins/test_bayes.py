"""Tests for the Bayes plug-in."""

import unittest
from tempfile import NamedTemporaryFile

import mock
from mock import MagicMock
from oa.plugins.bayes import BayesPlugin, Store
from oa.message import Message


def _make_mock_context(presets):
    """
    Construct a context mock instance that implements get_plugin_data() and
    set_plugin_data() with a simple global backing dict and the quirk that
    get_plugin_data() will return a value from the preset dict if the
    corresponding key exists there.
    """
    backing = {}
    ctx = MagicMock()

    def _get_plugin_effect(_, key):
        if key in presets:
            return presets[key]
        return backing[key]

    ctx.get_plugin_data.side_effect = _get_plugin_effect

    def _set_plugin_effect(_, key, value):
        backing[key] = value

    ctx.set_plugin_data.side_effect = _set_plugin_effect
    return ctx


class BayesTests(unittest.TestCase):
    """Test cases for the BayesPlugin class."""

    def setUp(self):
        self.global_data = {"use_bayes": True}
        self.mock_ctxt = _make_mock_context(self.global_data)
        engine = {
            "hostname":"",
            "user":"",
            "password":"",
            "db_name":"",
        }
        mock.patch("oa.plugins.bayes.BayesPlugin.get_engine", return_value=engine).start()

    def tearDown(self):
        mock.patch.stopall()

    def test_learn_message(self):
        """Test the learn_message method."""
        b = BayesPlugin(self.mock_ctxt)
        b.get_body_from_msg = lambda x: {}
        b.store = Store(b)
        b.store.tie_db_writeable = lambda: True
        ret = "test"
        msg = Message(self.mock_ctxt, "test message")
        isspam = True
        b._learn_trapped = mock.MagicMock(return_value=ret)
        b.learn_caller_will_untie = True
        result = b.learn_message(msg, isspam)
        self.assertEqual(ret, result)
        b._learn_trapped.assert_called_once_with(isspam, msg)

    def test_learn_message_no_bayes(self):
        """Test the learn_message method when bayes is not enabled."""
        b = BayesPlugin(self.mock_ctxt)
        b.store = Store(b)
        self.global_data["use_bayes"] = False
        result = b.learn_message(None, None)
        self.assertEqual(result, None)


class BayesDatabaseTest(unittest.TestCase):
    def test_empty_database(self):
        temp_file = NamedTemporaryFile()
        backing = {"bayes_sql_dsn": "sqlite:///{}".format(temp_file.name)}
        ctx = _make_mock_context(backing)
        b = BayesPlugin(ctx)
        b.finish_parsing_end(None)

        store = Store(b)
        store.tie_db_writeable()
        self.assertIsNone(store.seen_get("non-existent-id"))


def suite():
    """Gather all the tests from this package in a test suite."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(BayesTests, "test"))
    return test_suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
