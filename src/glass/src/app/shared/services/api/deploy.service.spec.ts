import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { DeployService } from '~/app/shared/services/api/deploy.service';

describe('DeployService', () => {
  let service: DeployService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(DeployService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call status', () => {
    service.status().subscribe();
    const req = httpTesting.expectOne('api/deploy/status');
    expect(req.request.method).toBe('GET');
  });

  it('should call install', () => {
    service
      .install({
        device: '/dev/sda'
      })
      .subscribe();
    const req = httpTesting.expectOne('api/deploy/install');
    expect(req.request.method).toBe('POST');
  });

  it('should call requirements', () => {
    service.requirements().subscribe();
    const req = httpTesting.expectOne('api/deploy/requirements');
    expect(req.request.method).toBe('GET');
  });

  it('should call devices', () => {
    service.devices().subscribe();
    const req = httpTesting.expectOne('api/deploy/devices');
    expect(req.request.method).toBe('GET');
  });

  it('should call create', () => {
    service
      .create({
        ntpaddr: 'test.test.test',
        hostname: 'foobar',
        storage: ['/dev/sdb', '&dev/sdc']
      })
      .subscribe();
    const req = httpTesting.expectOne('api/deploy/create');
    expect(req.request.method).toBe('POST');
  });

  it('should call token', () => {
    service.token().subscribe();
    const req = httpTesting.expectOne('api/deploy/token');
    expect(req.request.method).toBe('GET');
  });

  it('should call join', () => {
    service
      .join({
        address: 'foo',
        token: 'ABCD-0123-5A6B-98FE',
        hostname: 'foobar',
        storage: ['/dev/sdb', '&dev/sdc']
      })
      .subscribe();
    const req = httpTesting.expectOne('api/deploy/join');
    expect(req.request.method).toBe('POST');
  });
});
