// 前端认证辅助：JWT token 的存取与登录调用（SEC-001 前端配套）
export interface AuthUser {
  user_id: number
  username: string
  role: string
  supplier_id?: number | null
}

const TOKEN_KEY = 'sc_token'
const USER_KEY = 'sc_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getSession(): { token: string; user: AuthUser } | null {
  const token = localStorage.getItem(TOKEN_KEY)
  const raw = localStorage.getItem(USER_KEY)
  if (!token || !raw) return null
  try {
    return { token, user: JSON.parse(raw) as AuthUser }
  } catch {
    return null
  }
}

export function setSession(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

// 调用公开登录端点获取 JWT
export async function login(username: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const resp = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) {
    throw new Error('用户名或密码错误')
  }
  const data = await resp.json()
  return { token: data.access_token as string, user: data.user as AuthUser }
}
