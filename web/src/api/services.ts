import { apiClient, setStoredToken } from "./client";
import type { Role, Submission, SubmissionStatus, SurveyDetail, SurveySummary, UserAccount } from "./types";

export const authApi = {
  async login(email: string, password: string) {
    const { data } = await apiClient.post("/api/auth/login-json", { email, password });
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
};

export const surveysApi = {
  async list(statusFilter?: string): Promise<SurveySummary[]> {
    const { data } = await apiClient.get("/api/surveys", {
      params: statusFilter ? { status_filter: statusFilter } : undefined,
    });
    return data;
  },
  async get(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.get(`/api/surveys/${id}`);
    return data;
  },
  async create(payload: {
    title: string;
    description?: string;
    questions: any[];
    assigned_enumerator_ids?: string[];
  }): Promise<SurveyDetail> {
    const { data } = await apiClient.post("/api/surveys", payload);
    return data;
  },
  async update(
    id: string,
    payload: { title?: string; description?: string; questions?: any[]; assigned_enumerator_ids?: string[] }
  ): Promise<SurveyDetail> {
    const { data } = await apiClient.put(`/api/surveys/${id}`, payload);
    return data;
  },
  async publish(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.post(`/api/surveys/${id}/publish`);
    return data;
  },
  async unpublish(id: string): Promise<SurveyDetail> {
    const { data } = await apiClient.post(`/api/surveys/${id}/unpublish`);
    return data;
  },
  async archive(id: string): Promise<void> {
    await apiClient.delete(`/api/surveys/${id}`);
  },
};

export const submissionsApi = {
  async list(filters: { survey_id?: string; status?: SubmissionStatus }): Promise<Submission[]> {
    const { data } = await apiClient.get("/api/submissions", { params: filters });
    return data;
  },
  async get(id: string): Promise<Submission> {
    const { data } = await apiClient.get(`/api/submissions/${id}`);
    return data;
  },
};

export const usersApi = {
  async list(): Promise<UserAccount[]> {
    const { data } = await apiClient.get("/api/users");
    return data;
  },
  async create(payload: { full_name: string; email: string; password: string; role: Role }): Promise<UserAccount> {
    const { data } = await apiClient.post("/api/users", payload);
    return data;
  },
  async update(id: string, payload: Partial<{ full_name: string; role: Role; is_active: boolean; password: string }>) {
    const { data } = await apiClient.put(`/api/users/${id}`, payload);
    return data;
  },
  async deactivate(id: string): Promise<void> {
    await apiClient.delete(`/api/users/${id}`);
  },
};
