export interface ApiSuccessResponse<T> {
  success: true;
  message: string;
  data: T;
  meta?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  errors: unknown;
  error_code?: string;
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;
