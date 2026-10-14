// src/App.jsx
import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import SlicePage from "./pages/SlicePage";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <SlicePage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;