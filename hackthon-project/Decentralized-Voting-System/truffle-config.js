module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",     // Ganache GUI or CLI
      port: 7545,            // Ganache default port
      network_id: "*"        // Match any network id
    }
  },

  // Explicitly specify the compiler version
  compilers: {
    solc: {
      version: "0.5.16",   // Match your contracts' pragma
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        }
      }
    }
  }
};
