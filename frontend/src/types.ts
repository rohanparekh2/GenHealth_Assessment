export interface Order {
  id: string;
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
}

export interface CreateOrderRequest {
  patient_first_name: string;
  patient_last_name: string;
  date_of_birth: string;
}

export interface UpdateOrderRequest {
  patient_first_name?: string;
  patient_last_name?: string;
  date_of_birth?: string;
}

export interface UploadResponse {
  id?: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  raw_text_preview?: string;
}
