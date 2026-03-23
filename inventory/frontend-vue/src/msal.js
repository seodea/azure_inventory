import { PublicClientApplication } from "@azure/msal-browser";

export function createMsalInstance({ clientId, tenantId, redirectUri }) {
  const msalConfig = {
    auth: {
      clientId,
      authority: `https://login.microsoftonline.com/${tenantId}`,
      redirectUri: redirectUri || window.location.origin,
    },
  };

  return new PublicClientApplication(msalConfig);
}
