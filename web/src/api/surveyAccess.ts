import type { SurveySummary, UserAccount } from "./types";

type Actor = Pick<UserAccount, "id" | "role"> | null | undefined;

export function isStaff(user: Actor): boolean {
  return user?.role === "ADMINISTRATOR" || user?.role === "SUPERVISOR";
}

/**
 * Surveys whose results (submissions, analytics, exports) this user may look at.
 * Mirrors backend can_view_results(): staff see every listed survey; everyone
 * else sees only the personal surveys they own (which includes answers
 * collected by the people they shared the survey with).
 */
export function resultsSurveys(surveys: SurveySummary[], user: Actor): SurveySummary[] {
  if (!user) return [];
  if (isStaff(user)) return surveys;
  return surveys.filter((s) => s.scope === "PERSONAL" && s.created_by_id === user.id);
}
