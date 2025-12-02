import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-cv-navy text-white">
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-cv-teal mb-4">Today's Games</h1>
        <p className="text-gray-400">Dashboard - Game list will go here</p>
        
        {/* Placeholder for game cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-cv-navy border border-cv-blue p-6 rounded-lg">
            <p className="text-cv-teal font-semibold">Game Card Placeholder</p>
            <p className="text-sm text-gray-400 mt-2">UConn vs Stanford</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;