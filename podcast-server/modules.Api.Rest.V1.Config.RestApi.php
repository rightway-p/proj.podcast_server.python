<?php

declare(strict_types=1);

namespace Modules\Api\Rest\V1\Config;

use CodeIgniter\Config\BaseConfig;

class RestApi extends BaseConfig
{
    public bool $enabled = true;
    public bool $basicAuth = true;
    public ?string $basicAuthUsername = 'automation';
    public ?string $basicAuthPassword = 'automation';
    public int $limit = 100;
    public string $gateway = 'api/rest/v1/';
}
