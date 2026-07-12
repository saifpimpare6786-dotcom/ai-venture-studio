import React from 'react';
import BusinessIdeaWizard from './components/BusinessIdeaWizard';
import './App.css';

function App() {
  const handleSubmitSuccess = (data) => {
    console.log('Business Idea wizard submitted:', data);
  };

  return (
    <div className="relative min-h-screen">
      <BusinessIdeaWizard onSubmitSuccess={handleSubmitSuccess} />
    </div>
  );
}

export default App;
