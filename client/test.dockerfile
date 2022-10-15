FROM zokrates/zokrates:0.4.10

COPY ./ ./
ENV args 0
RUN ./zokrates compile -i circuits/mmr/zkRollUp2048.code
RUN ./zokrates setup
CMD ./zokrates compute-witness -a ${args} >/dev/null; ./zokrates generate-proof >/dev/null; sed -i -e '$a\' proof.json; cat proof.json;
