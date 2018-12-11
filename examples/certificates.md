## Create a Certificate Authority root (which represents this server)
------------------------------------------------------------------------
Organization & Common Name: Some human identifier for this server CA.

```
openssl genrsa -out ca.key 2048
```
```
openssl req -new -x509 -days 365 -key ca.key -out ca.crt
```

## Create the Client Key and CSR
------------------------------------------------------------------------
Organization & Common Name = website name / localhost
```
openssl genrsa -out client.key 2048
```
```
openssl req -new -key client.key -out client.csr
```
```
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out client.crt
```

## Convert Client Key to PKCS
------------------------------------------------------------------------
So that it may be installed in most browsers.
```
openssl pkcs12 -export -clcerts -in client.crt -inkey client.key -out client.p12
```

## Convert Client Key to (combined) PEM
------------------------------------------------------------------------
Combines client.crt and client.key into a single PEM file for programs using openssl.
```
openssl pkcs12 -in client.p12 -out client.pem -clcerts
```

## Install Client Key on client device (OS or browser)
------------------------------------------------------------------------
Use client.p12. Actual instructions vary.