$vaultName = "ShoalsAzureKeyVault"
$secretName = "ShoalsServicePrincipleSecret"

az login --identity

$secretValue = az keyvault secret show `
    --vault-name $vaultName `
    --name $secretName `
    --query value `
    -o tsv

powershell.exe -File "C:\Users\myAzVm\Documents\GitHub\Print-Promo\Azure_Uploader.ps1" `
    -ClientId "7ec3d88d-9f98-402e-b068-a6870f2e2fe5" `
    -ClientSecret $secretValue `
    -TenantId "dc60d618-0549-4543-b29c-aeaf89c13926" `
    -StorageAccount "shoalsdatalake" `
    -ContainerName "rawdata" `
    -SourcePath "C:\Users\myAzVm\Desktop\Inksoft" `
    -BlobPrefix "Inksoft/Orders"