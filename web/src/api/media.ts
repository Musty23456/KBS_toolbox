import { apiClient } from "./client";
import type { Submission } from "./types";

export type MediaKind = "PHOTO" | "AUDIO" | "SIGNATURE";

/** A file captured in the browser (voice note, photo, signature) waiting to be uploaded. */
export interface CapturedFile {
  blob: Blob;
  filename: string;
}

/** Answer row sent when creating a submission from the web form. */
export interface WebAnswerIn {
  question_id: string;
  value_text?: string | null;
  media_reference?: string | null;
  group_instance_index?: number | null;
}

export const webSubmissionsApi = {
  async create(payload: {
    client_submission_uuid: string;
    survey_id: string;
    survey_version_id: string;
    collected_at?: string;
    gps_latitude?: number | null;
    gps_longitude?: number | null;
    answers: WebAnswerIn[];
  }): Promise<Submission> {
    const { data } = await apiClient.post("/api/submissions", payload);
    return data;
  },
};

export const mediaApi = {
  /** Uploads one captured file and attaches it to the matching answer row. */
  async upload(params: {
    submissionId: string;
    questionId: string;
    kind: MediaKind;
    file: Blob;
    filename: string;
    groupInstanceIndex?: number | null;
  }): Promise<{ id: string; url: string }> {
    const form = new FormData();
    form.append("submission_id", params.submissionId);
    form.append("question_id", params.questionId);
    form.append("kind", params.kind);
    if (params.groupInstanceIndex !== undefined && params.groupInstanceIndex !== null) {
      form.append("group_instance_index", String(params.groupInstanceIndex));
    }
    form.append("file", params.file, params.filename);
    const { data } = await apiClient.post("/api/media/upload", form);
    return data;
  },

  /** Downloads a stored file (needs the login token, so a plain link would not work). */
  async fetchBlob(url: string): Promise<Blob> {
    const { data } = await apiClient.get(url, { responseType: "blob" });
    return data as Blob;
  },
};
