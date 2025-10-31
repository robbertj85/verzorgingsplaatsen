// Script to fetch Netherlands administrative boundaries
// Run with: node public/fetch-boundaries.js

const https = require('https');
const fs = require('fs');

// Fetch provinces from OpenStreetMap via Overpass API
const fetchProvinces = () => {
  const query = `
    [out:json][timeout:60];
    area["ISO3166-2"="NL"]->.nl;
    (
      relation["admin_level"="4"]["boundary"="administrative"](area.nl);
    );
    out geom;
  `;

  const options = {
    hostname: 'overpass-api.de',
    path: '/api/interpreter',
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    }
  };

  const req = https.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
      console.log('Provinces fetched');
      fs.writeFileSync('public/nl-provinces.json', data);
    });
  });

  req.on('error', (e) => console.error(e));
  req.write(`data=${encodeURIComponent(query)}`);
  req.end();
};

// Fetch municipalities
const fetchMunicipalities = () => {
  const query = `
    [out:json][timeout:90];
    area["ISO3166-2"="NL"]->.nl;
    (
      relation["admin_level"="8"]["boundary"="administrative"](area.nl);
    );
    out geom;
  `;

  const options = {
    hostname: 'overpass-api.de',
    path: '/api/interpreter',
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    }
  };

  const req = https.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
      console.log('Municipalities fetched');
      fs.writeFileSync('public/nl-municipalities.json', data);
    });
  });

  req.on('error', (e) => console.error(e));
  req.write(`data=${encodeURIComponent(query)}`);
  req.end();
};

console.log('Fetching provinces...');
fetchProvinces();

setTimeout(() => {
  console.log('Fetching municipalities...');
  fetchMunicipalities();
}, 5000);
