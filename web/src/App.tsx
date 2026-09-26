import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { PasswordResetRequestsPage } from "./pages/users/PasswordResetRequestsPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SurveyListPage } from "./pages/surveys/SurveyListPage";
import { SurveyBuilderPage } from "./pages/surveys/SurveyBuilderPage";
import { SubmissionsPage } from "./pages/submissions/SubmissionsPage";
import { UsersPage } from "./pages/users/UsersPage";
import { AnalyticsPage } from "./pages/analytics/AnalyticsPage";
import { DevicesPage } from "./pages/devices/DevicesPage";
import { MapPage } from "./pages/map/MapPage";
import { ExportPage } from "./pages/exports/ExportPage";
import { TranslationsPage } from "./pages/translations/TranslationsPage";
import { AuditPage } from "./pages/audit/AuditPage";
import { FillSurveyPage } from "./pages/surveys/FillSurveyPage";
import { AboutPage } from "./pages/AboutPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/forgot-password"
            element={<ForgotPasswordPage />}
          />

      

          {/* Protected application routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />

            <Route
              path="/surveys"
              element={<SurveyListPage />}
            />

            <Route
              path="/surveys/new"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <SurveyBuilderPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/surveys/:surveyId"
              element={<SurveyBuilderPage />}
            />

            <Route
              path="/surveys/:surveyId/fill"
              element={<FillSurveyPage />}
            />

            <Route
              path="/map"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <MapPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/exports"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <ExportPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/translations"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <TranslationsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/submissions"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <SubmissionsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/analytics"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/devices"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <DevicesPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/audit"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <AuditPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/about"
              element={<AboutPage />}
            />

            <Route
              path="/users"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR", "SUPERVISOR"]}
                >
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Unknown routes */}
          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
         <Route
              path="/password-reset-requests"
              element={
                <ProtectedRoute
                  allowedRoles={["ADMINISTRATOR"]}
                >
                  <PasswordResetRequestsPage />
                </ProtectedRoute>
              }
            />
