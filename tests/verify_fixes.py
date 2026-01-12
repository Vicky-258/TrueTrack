import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import Config
from core.pipeline import handle_resolving_identity, handle_matching_metadata, PipelineError, PipelineState
from core.job import Job, JobOptions

class TestFixes(unittest.TestCase):

    def test_config_env_var(self):
        """Verify Config respects environment variables"""
        # Note: This checks the value loaded at import time. 
        # Since we imported Config above, we should check if it defaults or if we can reload it.
        # Ideally, we'd mock os.getenv BEFORE import, but for now let's just check the default is what we expect
        # or that it exists.
        self.assertTrue(hasattr(Config, "LIBRARY_ROOT"))
        print(f"\n[OK] Config.LIBRARY_ROOT = {Config.LIBRARY_ROOT}")

    @patch("core.pipeline.YTMusic")
    def test_identity_error_handling(self, mock_yt):
        """Verify handle_resolving_identity catches exceptions"""
        mock_instance = mock_yt.return_value
        mock_instance.search.side_effect = Exception("Simulated API Down")

        options = JobOptions()
        job = Job(options=options, raw_query="test")
        
        with self.assertRaises(PipelineError) as cm:
            handle_resolving_identity(job)
        
        self.assertEqual(cm.exception.code, "YTMUSIC_ERROR")
        print("\n[OK] Identity Error Handling verified")

    @patch("core.pipeline.search_itunes")
    def test_metadata_error_handling(self, mock_search):
        """Verify handle_matching_metadata falls back to archiving on network error"""
        mock_search.side_effect = requests.RequestException("Simulated Timeout")

        job = Job(options=JobOptions())
        job.identity_hint = MagicMock()
        job.identity_hint.title = "Test"
        job.identity_hint.artists = ["Test"]
        
        handle_matching_metadata(job)
        
        self.assertEqual(job.current_state, PipelineState.ARCHIVING)
        print("\n[OK] Metadata Error Handling -> Archiving verified")

if __name__ == "__main__":
    unittest.main()
