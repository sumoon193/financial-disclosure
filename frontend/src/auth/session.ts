import Keycloak from 'keycloak-js'

const configured = Boolean(
  import.meta.env.VITE_KEYCLOAK_URL
  && import.meta.env.VITE_KEYCLOAK_REALM
  && import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
)

const keycloak = configured
  ? new Keycloak({
      url: import.meta.env.VITE_KEYCLOAK_URL!,
      realm: import.meta.env.VITE_KEYCLOAK_REALM!,
      clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID!,
    })
  : null

let accessToken: string | undefined

export function getAccessToken() {
  return accessToken
}

export function isOidcConfigured() {
  return configured
}

export async function initializeSession() {
  if (!keycloak) return false
  const authenticated = await keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
    checkLoginIframe: false,
    token: undefined,
    refreshToken: undefined,
  })
  accessToken = keycloak.token
  if (authenticated) {
    window.setInterval(async () => {
      if (await keycloak.updateToken(45)) accessToken = keycloak.token
    }, 30_000)
  }
  return authenticated
}

export function logout() {
  accessToken = undefined
  return keycloak?.logout({ redirectUri: window.location.origin })
}
