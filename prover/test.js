const web3 = require('web3')

const proof = require('./proof')

const abi = [
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": false,
          "name": "s",
          "type": "string"
        }
      ],
      "name": "Verified",
      "type": "event"
    },
    {
      "constant": false,
      "inputs": [
        {
          "name": "a",
          "type": "uint256[2]"
        },
        {
          "name": "b",
          "type": "uint256[2][2]"
        },
        {
          "name": "c",
          "type": "uint256[2]"
        },
        {
          "name": "input",
          "type": "uint256[8]"
        }
      ],
      "name": "verifyTx",
      "outputs": [
        {
          "name": "r",
          "type": "bool"
        }
      ],
      "payable": false,
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]
var accounts;
const 
accounts = web3.eth.getAccounts().then(function (acc) {accounts = acc});

const address = '0x05397AF51B1275362f7ef82b49A9daAFf921E01c'; // verifier contract address


let verifier = new web3.eth.Contract(abi, address, {
    from: accounts[0], // default from address
    gasPrice: '20000000000000' // default gas price in wei
});
async function check(){
let result = await verifier.methods
    .verifyTx(proof.proof.a, proof.proof.b, proof.proof.c,proof.inputs)
    .call({ from: accounts[0] });
    console.log(result)    
}

check()