/**
 * VigilLedger AI - Seed Data
 * Pre-populated accounts, historical double-entry bank transactions, fraud rules, and mule graph data.
 */

window.SeedData = {
  accounts: [
    { id: "ACC-883910", holder: "Acme International Corp", balance: 4850900.00, currency: "USD", type: "Corporate", homeCountry: "USA", homeCity: "New York", lat: 40.7128, lng: -74.0060, riskTier: "Low", status: "Active" },
    { id: "ACC-104928", holder: "Elena Rostova", balance: 14200.50, currency: "USD", type: "Personal Savings", homeCountry: "USA", homeCity: "Chicago", lat: 41.8781, lng: -87.6298, riskTier: "High", status: "Active" },
    { id: "ACC-501923", holder: "Apex Global Holdings LLC", balance: 12450000.00, currency: "EUR", type: "Investment", homeCountry: "DEU", homeCity: "Frankfurt", lat: 50.1109, lng: 8.6821, riskTier: "Low", status: "Active" },
    { id: "ACC-992011", holder: "Viktor Vasilev (Shell Account)", balance: 843900.00, currency: "USD", type: "Checking", homeCountry: "CYP", homeCity: "Limassol", lat: 34.6786, lng: 33.0413, riskTier: "Critical", status: "Under Review" },
    { id: "ACC-304912", holder: "Nexus Digital Assets Corp", balance: 92000.00, currency: "USD", type: "Fintech Escrow", homeCountry: "SGP", homeCity: "Singapore", lat: 1.3521, lng: 103.8198, riskTier: "Medium", status: "Active" },
    { id: "ACC-772109", holder: "Marcus Vance", balance: 3500.00, currency: "USD", type: "Personal", homeCountry: "USA", homeCity: "Miami", lat: 25.7617, lng: -80.1918, riskTier: "High", status: "Active" },
    { id: "ACC-661029", holder: "Panama Pacific Offshore Escrow", balance: 2980000.00, currency: "USD", type: "Offshore Wire", homeCountry: "PAN", homeCity: "Panama City", lat: 8.9824, lng: -79.5199, riskTier: "Critical", status: "Flagged" },
    { id: "ACC-449102", holder: "Sarah Jenkins", balance: 28400.00, currency: "USD", type: "Personal", homeCountry: "CAN", homeCity: "Toronto", lat: 43.6532, lng: -79.3832, riskTier: "Low", status: "Active" }
  ],

  rules: [
    {
      id: "RULE-AML-01",
      code: "STRUCTURING_SMURFING",
      name: "Smurfing / Structuring Detection",
      category: "AML Compliance",
      description: "Detects multiple transfers between $8,500 and $9,999 structured to evade the $10,000 CTR mandatory reporting threshold within a 24h window.",
      severity: "High",
      threshold: "$9,900 / 3 transfers",
      weight: 40,
      enabled: true
    },
    {
      id: "RULE-GEO-02",
      code: "IMPOSSIBLE_TRAVEL",
      name: "Geographic Velocity Anomaly",
      category: "Location Security",
      description: "Flags sequential transactions from IP locations physical distance implies impossible speed (>800 km/h) without commercial flight gap.",
      severity: "Critical",
      threshold: "> 800 km/h",
      weight: 45,
      enabled: true
    },
    {
      id: "RULE-VEL-03",
      code: "HIGH_VELOCITY_RAPID_WIRE",
      name: "Rapid Wire Transfer Cascade",
      category: "Behavioral AI",
      description: "Triggers when an account executes > 3 high-value outbound transfers within 10 minutes, characteristic of account takeover cashouts.",
      severity: "High",
      threshold: "> 3 tx / 10 min",
      weight: 35,
      enabled: true
    },
    {
      id: "RULE-SAN-04",
      code: "OFAC_SANCTION_LIST",
      name: "FATF / OFAC High Risk Jurisdiction",
      category: "Sanctions",
      description: "Immediate critical flag for any wire origin, destination, or intermediary bank routing through sanctioned or FATF blacklisted jurisdictions.",
      severity: "Critical",
      threshold: "Sanctioned Entity Match",
      weight: 50,
      enabled: true
    },
    {
      id: "RULE-MUL-05",
      code: "MULE_FAN_OUT_NETWORK",
      name: "Mule Account Fan-Out Pattern",
      category: "Graph Analytics",
      description: "Detects intermediary accounts receiving rapid micro-deposits from multiple distinct senders followed by immediate consolidation outbound.",
      severity: "Critical",
      threshold: "Fan-in > 4, Fan-out = 1",
      weight: 45,
      enabled: true
    },
    {
      id: "RULE-DEV-06",
      code: "NEW_DEVICE_TOR_PROXY",
      name: "Anonymous Proxy & Device Switch",
      category: "Device Fingerprint",
      description: "Flags transactions originating from TOR exit nodes, residential proxies, or completely unseen hardware device fingerprints.",
      severity: "Medium",
      threshold: "Proxy = True OR Unseen Hardware",
      weight: 25,
      enabled: true
    }
  ],

  transactions: [
    {
      id: "TX-904128",
      timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
      debitAccount: "ACC-104928",
      debitHolder: "Elena Rostova",
      creditAccount: "ACC-992011",
      creditHolder: "Viktor Vasilev (Shell Account)",
      amount: 9850.00,
      currency: "USD",
      channel: "Wire SWIFT",
      ipAddress: "185.220.101.4", // TOR exit node
      location: "Limassol, Cyprus",
      lat: 34.6786,
      lng: 33.0413,
      deviceFingerprint: "fp_chrome_mac_8f91a",
      riskScore: 88,
      riskLevel: "Critical",
      status: "Flagged",
      triggers: ["STRUCTURING_SMURFING", "NEW_DEVICE_TOR_PROXY"],
      reasons: [
        "Structuring / Smurfing pattern ($9,850 transfer near $10k threshold)",
        "Known anonymizing TOR Proxy IP Address",
        "High-risk destination entity in Cyprus"
      ],
      blockIndex: 1042,
      previousHash: "0000a3b8f1c9d2e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8",
      hash: "0000f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5"
    },
    {
      id: "TX-904127",
      timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
      debitAccount: "ACC-104928",
      debitHolder: "Elena Rostova",
      creditAccount: "ACC-992011",
      creditHolder: "Viktor Vasilev (Shell Account)",
      amount: 9700.00,
      currency: "USD",
      channel: "Wire SWIFT",
      ipAddress: "185.220.101.4",
      location: "Limassol, Cyprus",
      lat: 34.6786,
      lng: 33.0413,
      deviceFingerprint: "fp_chrome_mac_8f91a",
      riskScore: 82,
      riskLevel: "High",
      status: "Flagged",
      triggers: ["STRUCTURING_SMURFING"],
      reasons: [
        "2nd transfer under $10,000 threshold within 1 hour",
        "Destination account flagged for suspicious activity"
      ],
      blockIndex: 1041,
      previousHash: "00007c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d",
      hash: "0000a3b8f1c9d2e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8"
    },
    {
      id: "TX-904126",
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      debitAccount: "ACC-883910",
      debitHolder: "Acme International Corp",
      creditAccount: "ACC-501923",
      creditHolder: "Apex Global Holdings LLC",
      amount: 250000.00,
      currency: "USD",
      channel: "ACH B2B",
      ipAddress: "198.51.100.22",
      location: "New York, USA",
      lat: 40.7128,
      lng: -74.0060,
      deviceFingerprint: "fp_corp_srv_9921",
      riskScore: 12,
      riskLevel: "Low",
      status: "Approved",
      triggers: [],
      reasons: ["Verified corporate partner transaction", "Authorized corporate IP range"],
      blockIndex: 1040,
      previousHash: "00001a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f",
      hash: "00007c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d"
    },
    {
      id: "TX-904125",
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      debitAccount: "ACC-772109",
      debitHolder: "Marcus Vance",
      creditAccount: "ACC-661029",
      creditHolder: "Panama Pacific Offshore Escrow",
      amount: 495000.00,
      currency: "USD",
      channel: "Wire SWIFT",
      ipAddress: "190.140.22.91",
      location: "Panama City, Panama",
      lat: 8.9824,
      lng: -79.5199,
      deviceFingerprint: "fp_android_unrecognized",
      riskScore: 94,
      riskLevel: "Critical",
      status: "Frozen",
      triggers: ["IMPOSSIBLE_TRAVEL", "OFAC_SANCTION_LIST", "HIGH_VELOCITY_RAPID_WIRE"],
      reasons: [
        "Impossible Travel Anomaly: Previous login in Miami 15 mins prior (Speed: 3,200 km/h)",
        "Unrecognized Android device hardware fingerprint",
        "High-risk offshore escrow entity destination"
      ],
      blockIndex: 1039,
      previousHash: "00009f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a",
      hash: "00001a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f"
    },
    {
      id: "TX-904124",
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      debitAccount: "ACC-449102",
      debitHolder: "Sarah Jenkins",
      creditAccount: "ACC-304912",
      creditHolder: "Nexus Digital Assets Corp",
      amount: 3200.00,
      currency: "USD",
      channel: "Mobile P2P",
      ipAddress: "142.250.190.46",
      location: "Toronto, Canada",
      lat: 43.6532,
      lng: -79.3832,
      deviceFingerprint: "fp_iphone_14_sj",
      riskScore: 18,
      riskLevel: "Low",
      status: "Approved",
      triggers: [],
      reasons: ["Normal consumer purchasing activity", "Matches historical device pattern"],
      blockIndex: 1038,
      previousHash: "00003b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c",
      hash: "00009f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a"
    }
  ],

  // Graph Data for Mule Network Analysis
  muleNetwork: {
    nodes: [
      { id: "ACC-104928", label: "Elena Rostova (Victim)", type: "victim", x: 150, y: 180, risk: "High", country: "USA" },
      { id: "ACC-772109", label: "Marcus Vance (Victim)", type: "victim", x: 150, y: 340, risk: "High", country: "USA" },
      { id: "ACC-992011", label: "Viktor Vasilev (Mule Hub)", type: "mule", x: 420, y: 260, risk: "Critical", country: "CYP" },
      { id: "ACC-661029", label: "Panama Pacific (Cashout Sink)", type: "sink", x: 700, y: 260, risk: "Critical", country: "PAN" },
      { id: "ACC-304912", label: "Nexus Escrow", type: "neutral", x: 420, y: 440, risk: "Medium", country: "SGP" }
    ],
    edges: [
      { source: "ACC-104928", target: "ACC-992011", amount: "$19,550", txCount: 2, status: "Flagged" },
      { source: "ACC-772109", target: "ACC-992011", amount: "$45,000", txCount: 1, status: "Flagged" },
      { source: "ACC-992011", target: "ACC-661029", amount: "$495,000", txCount: 1, status: "Frozen" },
      { source: "ACC-772109", target: "ACC-304912", amount: "$3,200", txCount: 1, status: "Approved" }
    ]
  }
};
