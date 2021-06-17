import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { NodesService } from '~/app/shared/services/api/nodes.service';

describe('NodesService', () => {
  let service: NodesService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(NodesService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call start', () => {
    service
      .join({
        address: 'foo',
        token: 'ABCD-0123-5A6B-98FE',
        hostname: 'foobar'
      })
      .subscribe();
    const req = httpTesting.expectOne('api/nodes/join');
    expect(req.request.method).toBe('POST');
  });

  it('should call token', () => {
    service.token().subscribe();
    const req = httpTesting.expectOne('api/nodes/token');
    expect(req.request.method).toBe('GET');
  });

  it('should call deployment start', () => {
    service
      .deploymentStart({
        ntpaddr: 'test.test.test',
        hostname: 'foobar'
      })
      .subscribe();
    const req = httpTesting.expectOne('api/nodes/deployment/start');
    expect(req.request.method).toBe('POST');
  });

  it('should call deployment status', () => {
    service.deploymentStatus().subscribe();
    const req = httpTesting.expectOne('api/nodes/deployment/status');
    expect(req.request.method).toBe('GET');
  });

  it('should call deployment disk solution', () => {
    service.deploymentDiskSolution().subscribe();
    const req = httpTesting.expectOne('api/nodes/deployment/disksolution');
    expect(req.request.method).toBe('GET');
  });
});
