export interface WhoisInfo {
  domain: string;
  registrar?: string;
  creation_date?: string;
  expiration_date?: string;
  updated_date?: string;
  nameservers: string[];
  status: string[];
  dnssec?: string;
  raw_output: string;
}

export interface Contact {
  name?: string;
  organization?: string;
  email?: string;
  phone?: string;
}
