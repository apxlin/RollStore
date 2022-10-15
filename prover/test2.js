
const Web3 = require('web3');
const proof = require('./proof')

// 前面需要引入web3模块
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

const web3 = new Web3('http://127.0.0.1:7545');
const address = '0x05397AF51B1275362f7ef82b49A9daAFf921E01c';

class ContractCaller {
    
    // 新版本需要用异步等待
    async checkTest() {
        const accounts = await web3.eth.getAccounts();

        let Verifier = new web3.eth.Contract(abi, address, {
            from: accounts[0], // default from address
            gasPrice: '20000000000000' // default gas price in wei
        });



        // 发起交易，如果出错则打印错误信息，否则打印一下交易结果
        const result = await Verifier.methods.verifyTx(proof.proof.a, proof.proof.b, proof.proof.c,proof.inputs).call({ from: accounts[0] });

        console.log(result);
    }
}
// 调用方法
new ContractCaller().checkTest();

