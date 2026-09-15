export type Role = "ADMINISTRATOR" | "SUPERVISOR" | "ENUMERATOR";

export type SurveyStatus = "DRAFT" | "PUBLISHED" | "ARCHIVED";

export type QuestionType =
  | "SHORT_TEXT"
  | "LONG_TEXT"
  | "INTEGER"
  | "DECIMAL"
  | "DATE"
  | "TIME"
  | "DATETIME"
  | "SINGLE_CHOICE"
  | "MULTIPLE_CHOICE"
  | "DROPDOWN"
  | "YES_NO"
  | "GPS"
  | "PHOTO"
  | "AUDIO"
  | "SIGNATURE"
  | "BARCODE";

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  SHORT_TEXT: "Short text",
  LONG_TEXT: "Long text",
  INTEGER: "Integer",
  DECIMAL: "Decimal",
  DATE: "Date",
  TIME: "Time",
  DATETIME: "Date and time",
  SINGLE_CHOICE: "Single choice",
  MULTIPLE_CHOICE: "Multiple choice",
  DROPDOWN: "Dropdown",
  YES_NO: "Yes / No",
  GPS: "GPS location",
  PHOTO: "Photo",
  AUDIO: "Audio",
  SIGNATURE: "Signature",
  BARCODE: "Barcode / QR code",
};

export const CHOICE_TYPES: QuestionType[] = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "DROPDOWN"];

export interface Choice {
  id?: string;
  value: string;
  label: string;
  order_index: number;
  cascade_parent_value?: string | null;
}

export interface Question {
  id?: string;
  code: string;
  label: string;
  hint?: string | null;
  type: QuestionType;
  order_index: number;
  is_required: boolean;
  min_value?: number | null;
  max_value?: number | null;
  min_length?: number | null;
  max_length?: number | null;
  regex_pattern?: string | null;
  relevance_expression?: string | null;
  calculation_expression?: string | null;
  default_value?: string | null;
  cascade_parent_question_id?: string | null;
  choices: Choice[];
}

export interface SurveySummary {
  id: string;
  title: string;
  description: string | null;
  status: SurveyStatus;
  created_at: string;
  current_version_number: number | null;
  current_version_id: string | null;
}

export interface SurveyDetail extends SurveySummary {
  questions: Question[];
}

export interface UserAccount {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export type SubmissionStatus = "PENDING" | "UPLOADING" | "UPLOADED" | "SYNCED" | "FAILED";

export interface SubmissionAnswer {
  id: string;
  question_id: string;
  value_text: string | null;
  media_reference: string | null;
}

export interface Submission {
  id: string;
  survey_id: string;
  survey_version_id: string;
  submitted_by_id: string;
  client_submission_uuid: string;
  status: SubmissionStatus;
  gps_latitude: number | null;
  gps_longitude: number | null;
  collected_at: string | null;
  synced_at: string | null;
  created_at: string;
  answers: SubmissionAnswer[];
}
