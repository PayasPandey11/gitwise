import unittest
from unittest.mock import patch, MagicMock
import sys

from gitwise.cli.init import install_provider_dependencies


class TestDependencyInstallation(unittest.TestCase):
    """Test the dependency installation functionality."""

    @patch('subprocess.check_call')
    def test_install_google_dependencies(self, mock_check_call):
        """Test installing Google dependencies."""
        # Mock the subprocess.check_call to avoid actual installation
        mock_check_call.return_value = 0
        
        # Call the function
        result = install_provider_dependencies("google")
        
        # Check that the function returned True (success)
        self.assertTrue(result)
        
        # Check that check_call was called with the correct arguments
        mock_check_call.assert_called_once()
        args, _ = mock_check_call.call_args
        self.assertEqual(args[0][:3], [sys.executable, "-m", "pip"])
        self.assertEqual(args[0][3], "install")
        self.assertIn("google-generativeai", args[0][4])

    @patch('subprocess.check_call')
    def test_install_openai_dependencies(self, mock_check_call):
        """Test installing OpenAI dependencies."""
        mock_check_call.return_value = 0
        result = install_provider_dependencies("openai")
        self.assertTrue(result)
        mock_check_call.assert_called_once()
        args, _ = mock_check_call.call_args
        self.assertIn("openai", args[0][4])

    @patch('subprocess.check_call')
    def test_install_anthropic_dependencies(self, mock_check_call):
        """Test installing Anthropic dependencies."""
        mock_check_call.return_value = 0
        result = install_provider_dependencies("anthropic")
        self.assertTrue(result)
        mock_check_call.assert_called_once()
        args, _ = mock_check_call.call_args
        self.assertIn("anthropic", args[0][4])

    @patch('subprocess.check_call')
    def test_install_unknown_provider(self, mock_check_call):
        """Test installing dependencies for an unknown provider."""
        # Should return True without calling subprocess
        result = install_provider_dependencies("unknown_provider")
        self.assertTrue(result)
        mock_check_call.assert_not_called()

    @patch('subprocess.check_call')
    def test_installation_failure(self, mock_check_call):
        """Test handling of installation failure."""
        # Simulate a failed installation
        mock_check_call.side_effect = Exception("Installation failed")
        
        # Should return False on failure
        result = install_provider_dependencies("google")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 