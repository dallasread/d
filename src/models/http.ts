export interface HttpRedirect {
  from_url: string;
  to_url: string;
  status_code: number;
  response_time: number;
}

export interface HttpResponse {
  url: string;
  status_code: number;
  final_url: string;
  redirects: HttpRedirect[];
  headers: Record<string, string>;
  response_time: number;
  raw_output?: string;
}
