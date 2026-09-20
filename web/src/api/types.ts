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

export interface QuestionGroup {
  id?: string;
  title: string;
  description?: string | null;
  order_index: number;
  section_id?: string | null;
  repeatable: boolean;
  min_repeats: number;
  max_repeats?: number | null;
}

export interface SurveySection {
  id?: string;
  title: string;
  description?: string | null;
  order_index: number;
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
  section_id?: string | null;
  group_id?: string | null;
}

export interface SurveySummary {
  id: string;
  title: string;
  description: string | null;
  status: SurveyStatus;
  created_at: string;
  current_version_number: number | null;
  current_version_id: string | null;
  assigned_enumerator_ids: string[];
}

export interface SurveyDetail extends SurveySummary {
  sections: SurveySection[];
  groups: QuestionGroup[];
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
export type ReviewStatus = "RECEIVED" | "UNDER_REVIEW" | "HAS_ISSUES" | "APPROVED" | "REJECTED" | "RESUBMIT";

export interface SubmissionAnswer {
  id: string;
  question_id: string;
  value_text: string | null;
  media_reference: string | null;
  group_instance_index?: number | null;
}

export interface SubmissionReview {
  id: string;
  submission_id: string;
  reviewer_id: string;
  status: ReviewStatus;
  comment: string | null;
  created_at: string;
  updated_at: string;
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
  review_status: ReviewStatus;
  reviews: SubmissionReview[];
}


export interface Device {
  id: string; device_id: string; user_id: string; app_version: string | null; platform: string;
  last_seen_at: string | null; last_sync_at: string | null; last_sync_status: string | null;
  failed_sync_count: number; sync_requested_at: string | null; is_active: boolean; note: string | null;
}

export interface SubmissionMapPoint {
  id: string;
  survey_id: string;
  survey_title: string;
  submitted_by_id: string;
  latitude: number;
  longitude: number;
  collected_at: string | null;
  status: string;
}


export interface Translation {
  id: string;
  entity_type: "SURVEY" | "SECTION" | "GROUP" | "QUESTION" | "CHOICE";
  entity_id: string;
  field: "title" | "description" | "label" | "hint";
  language_code: string;
  value: string;
}
