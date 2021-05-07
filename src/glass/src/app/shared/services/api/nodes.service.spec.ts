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

  it('should call join', () => {
    service.join({ addr: 'foo', token: 'ABCD-0123-5A6B-98FE' }).subscribe();
    const req = httpTesting.expectOne('api/nodes/join');
    expect(req.request.method).toBe('POST');
  });

  it('should call token', () => {
    service.token().subscribe();
    const req = httpTesting.expectOne('api/nodes/token');
    expect(req.request.method).toBe('GET');
  });

  it('should call start', () => {
    service.bootstrapStart().subscribe();
    const req = httpTesting.expectOne('api/nodes/bootstrap/start');
    expect(req.request.method).toBe('POST');
  });

  it('should call status', () => {
    service.bootstrapStatus().subscribe();
    const req = httpTesting.expectOne('api/nodes/bootstrap/status');
    expect(req.request.method).toBe('GET');
  });
});
