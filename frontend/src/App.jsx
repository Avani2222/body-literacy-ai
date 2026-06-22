import { useState } from "react";
import React from "react";
import {BrowserRouter, Routes, Route, Link} from "react-router-dom";
import Login from "./Login.jsx";
import Signup from "./Signup.jsx";
import Dashboard from "./Dashboard.jsx";


function Landing(){
  return (
    <div style={{padding: 20}}>
      <h1>Welcome to Body Literacy AI</h1>
      <p><Link to="/login">Log In</Link> or <Link to="/signup">Sign Up</Link> to get started.</p>
    </div>
  );
}

export default function RouterApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/Login" element={<Login />} />
        <Route path="/Signup" element={<Signup />} />
        <Route path="/Dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
// The old App form was removed; RouterApp is the SPA root.xz