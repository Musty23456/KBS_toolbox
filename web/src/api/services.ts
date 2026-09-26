import { apiClient, setStoredToken } from "./client";
import type {
  Role,
  Submission,
  SubmissionStatus,
  SurveyDetail,
  SurveySummary,
  UserAccount,
  Device,
} from "./types";

/* =========================================================
   AUTH API
========================================================= */

export const authApi = {
  async register(payload: {
    full_name: string;
    email: string;
    password: string;
  }): Promise<UserAccount> {
    const { data } = await apiClient.post("/api/auth/register", payload);
    return data;
  },

  async login(email: string, password: string) {
    const { data } = await apiClient.post("/api/auth/login-json", {
      email,
      password,
    });

    setStoredToken(data.access_token);
    return data;
  },

  async logout() {
    try {
      await apiClient.post("/api/auth/logout");
    } finally {
      setStoredToken(null);
    }
  },

  async me(): Promise<UserAccount> {
    const { data } = await apiClient.get("/api/auth/me");
    return data;
  },

  async forgotPassword(email: string) {
    const { data } = await apiClient.post(
      "/api/auth/forgot-password",
      {
        email,
      }
    );

    return data;
  },

  async resetPassword(
    token: string,
    newPassword: string
  ) {
    const { data } = await apiClient.post(
      "/api/auth/reset-password",
      {
        token,
        new_password: newPassword,
      }
    );

    return data;
  },
};


/* =========================================================
   SURVEYS API
========================================================= */

export const surveysApi = {
  async list(
    statusFilter?: string
  ): Promise<SurveySummary[]> {
    const { data } = await apiClient.get("/api/surveys", {
      params: statusFilter
        ? { status_filter: statusFilter }
        : undefined,
    });

    return data;
  },

  async get(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.get(
      `/api/surveys/${id}`
    );

    return data;
  },

  async create(payload: {
    title: string;
    description?: string;
    questions: any[];
    sections?: any[];
    groups?: any[];
    assigned_enumerator_ids?: string[];
  }): Promise<SurveyDetail> {
    const { data } = await apiClient.post(
      "/api/surveys",
      payload
    );

    return data;
  },

  async update(
    id: string,
    payload: {
      title?: string;
      description?: string;
      questions?: any[];
      sections?: any[];
      groups?: any[];
      assigned_enumerator_ids?: string[];
    }
  ): Promise<SurveyDetail> {
    const { data } = await apiClient.put(
      `/api/surveys/${id}`,
      payload
    );

    return data;
  },

  async publish(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.post(
      `/api/surveys/${id}/publish`
    );

    return data;
  },

  async unpublish(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.post(
      `/api/surveys/${id}/unpublish`
    );

    return data;
  },

  async archive(id: string): Promise<void> {
    await apiClient.delete(`/api/surveys/${id}`);
  },
};


/* =========================================================
   SUBMISSIONS API
========================================================= */

export const submissionsApi = {
  async review(
    id: string,
    payload: {
      status: string;
      comment?: string;
    }
  ) {
    const { data } = await apiClient.post(
      `/api/submissions/${id}/review`,
      payload
    );

    return data;
  },

  async create(payload: {
    client_submission_uuid: string;
    survey_id: string;
    survey_version_id: string;
    collected_at?: string;
    gps_latitude?: number | null;
    gps_longitude?: number | null;
    answers: {
      question_id: string;
      value_text?: string | null;
    }[];
  }): Promise<Submission> {
    const { data } = await apiClient.post(
      "/api/submissions",
      payload
    );

    return data;
  },

  async list(filters: {
    survey_id?: string;
    status?: SubmissionStatus;
  }): Promise<Submission[]> {
    const { data } = await apiClient.get(
      "/api/submissions",
      {
        params: filters,
      }
    );

    return data;
  },

  async get(id: string): Promise<Submission> {
    const { data } = await apiClient.get(
      `/api/submissions/${id}`
    );

    return data;
  },
};


/* =========================================================
   USERS API
========================================================= */

export const usersApi = {
  async list(): Promise<UserAccount[]> {
    const { data } = await apiClient.get("/api/users");
    return data;
  },

  async create(payload: {
    full_name: string;
    email: string;
    password: string;
    role: Role;
  }): Promise<UserAccount> {
    const { data } = await apiClient.post(
      "/api/users",
      payload
    );

    return data;
  },

  async update(
    id: string,
    payload: Partial<{
      full_name: string;
      role: Role;
      is_active: boolean;
      password: string;
    }>
  ) {
    const { data } = await apiClient.put(
      `/api/users/${id}`,
      payload
    );

    return data;
  },

  async deactivate(id: string): Promise<void> {
    await apiClient.delete(`/api/users/${id}`);
  },
};


/* =========================================================
   DEVICES API
========================================================= */

export const devicesApi = {
  async list(): Promise<Device[]> {
    const { data } = await apiClient.get("/api/devices");
    return data;
  },

  async requestSync(deviceId: string): Promise<Device> {
    const { data } = await apiClient.post(
      `/api/devices/${deviceId}/request-sync`
    );

    return data;
  },

  async deactivate(deviceId: string): Promise<Device> {
    const { data } = await apiClient.post(
      `/api/devices/${deviceId}/deactivate`
    );

    return data;
  },
};


/* =========================================================
   MAP API
========================================================= */

export const mapApi = {
  async submissionPoints(
    filters?: {
      survey_id?: string;
      status?: string;
    }
  ): Promise<
    import("./types").SubmissionMapPoint[]
  > {
    const { data } = await apiClient.get(
      "/api/map/submissions",
      {
        params: filters,
      }
    );

    return data;
  },
};


/* =========================================================
   EXPORTS API
========================================================= */

export const exportsApi = {
  async download(
    format: "csv" | "json" | "xlsx" | "pdf",
    filters: {
      survey_id?: string;
      status?: string;
      submitted_by_id?: string;
      date_from?: string;
      date_to?: string;
    } = {}
  ) {
    const response = await apiClient.get(
      `/api/exports/${format}`,
      {
        params: filters,
        responseType: "blob",
      }
    );

    const contentType = String(
      response.headers["content-type"] ||
        "application/octet-stream"
    );

    const blob = new Blob(
      [response.data],
      {
        type: contentType,
      }
    );

    const url =
      window.URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;

    link.download =
      `kbs-submissions.${
        format === "xlsx"
          ? "xlsx"
          : format
      }`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(url);
  },
};


/* =========================================================
   ANALYTICS API
========================================================= */

export const analyticsApi = {
  async overview(
    filters: {
      survey_id?: string;
      date_from?: string;
      date_to?: string;
    } = {}
  ) {
    const { data } = await apiClient.get(
      "/api/analytics/overview",
      {
        params: filters,
      }
    );

    return data;
  },

  async questions(
    surveyId: string,
    questionId?: string
  ) {
    const { data } = await apiClient.get(
      "/api/analytics/questions",
      {
        params: {
          survey_id: surveyId,
          question_id: questionId,
        },
      }
    );

    return data;
  },
};


/* =========================================================
   TRANSLATIONS API
========================================================= */

export const translationsApi = {
  async languages(): Promise<
    {
      code: string;
      name: string;
    }[]
  > {
    const { data } = await apiClient.get(
      "/api/surveys/languages"
    );

    return data;
  },

  async list(
    surveyId: string
  ): Promise<
    import("./types").Translation[]
  > {
    const { data } = await apiClient.get(
      `/api/surveys/${surveyId}/translations`
    );

    return data;
  },

  async upsert(
    surveyId: string,
    payload: Omit<
      import("./types").Translation,
      "id"
    >
  ): Promise<
    import("./types").Translation
  > {
    const { data } = await apiClient.put(
      `/api/surveys/${surveyId}/translations`,
      payload
    );

    return data;
  },
};


/* =========================================================
   AUDIT API
========================================================= */

export const auditApi = {
  async summary(
    filters: {
      date_from?: string;
      date_to?: string;
    } = {}
  ) {
    const { data } = await apiClient.get(
      "/api/audit/summary",
      {
        params: filters,
      }
    );

    return data;
  },

  async logs(
    filters: {
      action?: string;
      entity_type?: string;
      actor_id?: string;
      search?: string;
      date_from?: string;
      date_to?: string;
      page?: number;
      page_size?: number;
    } = {}
  ) {
    const { data } = await apiClient.get(
      "/api/audit/logs",
      {
        params: filters,
      }
    );

    return data;
  },

  async filters() {
    const { data } = await apiClient.get(
      "/api/audit/filters"
    );

    return data;
  },
};
