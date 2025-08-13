param (
    [string]$ClientId,
    [string]$ClientSecret,
    [string]$TenantId,
    [string]$StorageAccount,
    [string]$ContainerName,
    [string]$SourcePath,
    [string]$BlobPrefix
)

# Authenticate to Azure using service principal
Write-Host "Authenticating to Azure..."
az login --service-principal `
    --username $ClientId `
    --password $ClientSecret `
    --tenant $TenantId | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Azure login failed. Check credentials and tenant ID."
    exit 1
}

# Upload files to blob container under specified path
Write-Host "Uploading files to blob path '$BlobPrefix'..."
az storage blob upload-batch `
    --account-name $StorageAccount `
    --destination $ContainerName `
    --source $SourcePath `
    --destination-path $BlobPrefix `
    --auth-mode login `
    --overwrite

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload complete."
} else {
    Write-Error "Upload failed."
}