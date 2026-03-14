import apiClient from './client'

export interface ImportRowError {
  row: number
  field: string
  message: string
}

export interface ImportPreviewResponse {
  valid_count: number
  error_count: number
  errors: ImportRowError[]
  duplicates: string[]
}

export const importApi = {
  async preview(file: File): Promise<ImportPreviewResponse> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<ImportPreviewResponse>('/projects/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async confirm(file: File): Promise<ImportPreviewResponse> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<ImportPreviewResponse>(
      '/projects/import?confirm=true',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return data
  },

  downloadTemplate() {
    window.open(`${apiClient.defaults.baseURL}/projects/template`, '_blank')
  },
}
