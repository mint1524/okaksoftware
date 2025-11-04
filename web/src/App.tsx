import { Route, Routes } from "react-router-dom";

import TokenPage from "./pages/TokenPage";

const App = () => {
  return (
    <Routes>
      <Route path=":token" element={<TokenPage />} />
      <Route path="*" element={<TokenPage />} />
    </Routes>
  );
};

export default App;
