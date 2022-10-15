var contractJson = require('./Verifier.json')
var Verifier = contract(contractJson);
const dataset = require('./proof')
// const ZkRollUp2 = artifacts.require('Verifier')
// contract('Verifier', async ([...users]) => {
//     let verifier
//     let dataset
    
    
    
//     it('Roll Up 2 items to the Pedersen Merkle Mountain Range', async () => {
//       verifier = await ZkRollUp2.deployed()
//       dataset = rollUp2Proof
//       let result = await verifier.verifyTx(dataset.proof.a, dataset.proof.b, dataset.proof.c, dataset.inputs)
//       console.log(result);
//     })
//   })
SimpleNameRegistry
  .deployed()
  .then(function(instance) {
     return instance.verifyTx(dataset.proof.a, dataset.proof.b, dataset.proof.c, dataset.inputs);
   })
  .then(function(result) {
    // If this callback is called, the transaction was successfully processed.
    alert("Transaction successful!")
  })
  .catch(function(e) {
    // There was an error! Handle it.
  });