import { request } from './client'

/** The fixed category vocabulary (defined once on the backend). */
export async function getCategories(): Promise<string[]> {
  const data = await request<{ items: string[] }>('/categories')
  return data.items
}
