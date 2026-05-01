"""ADK entrypoint for Shipwright.

The domain workflows live in ``shipwright.services`` so they can be tested
without Google credentials. When ADK is installed, this file exposes a real
multi-agent hierarchy for ``adk web`` / Cloud Run deployment. In local test
environments without ADK, it falls back to a lightweight spec object.
"""

from shipwright.adk_app import create_root_agent

root_agent = create_root_agent()
