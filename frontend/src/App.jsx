import { useEffect, useState } from "react";

function App() {

  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000")
    .then((res) => res.json())
    .then((data) => setMessage(data.message))
    .catch((err) => setMessage("Error: " + err.message))
  },[])

  return(
    <div className="min-h-screen flex items-center justify-center">
      <h1 className="text-2xl font-bold text-blue-500">{message}</h1>
    </div>
  );
}

export default App;