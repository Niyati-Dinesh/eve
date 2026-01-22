import React from 'react'
import Home from './components/Home/Home'
import Navbar from './components/Navigation/Navbar'
import ProblemSt from './components/Home/ProblemSt'

export default function App() {
  return (
    <div>
      <Navbar/>
      <Home/>
      <ProblemSt/>
    </div>
  )
}
