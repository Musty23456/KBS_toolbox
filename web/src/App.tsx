import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SurveyListPage } from "./pages/surveys/SurveyListPage";
import { SurveyBuilderPage } from "./pages/surveys/SurveyBuilderPage";
import { SubmissionsPage } from "./pages/submissions/SubmissionsPage";
import { UsersPage } from "./pages/users/UsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/surveys" element={<SurveyListPage />} />
            <Route
              path="/surveys/new"
              element={
                <ProtectedRoute allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}>
                  <SurveyBuilderPage />
                </ProtectedRoute>
              }
            />
            <Route path="/surveys/:surveyId" element={<SurveyBuilderPage />} />
            <Route
              path="/submissions"
              element={
                <ProtectedRoute allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}>
                  <SubmissionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
