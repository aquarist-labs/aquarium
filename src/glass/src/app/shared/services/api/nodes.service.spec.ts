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

  it('should call deployment disk solution', () => {
    service.deploymentDiskSolution().subscribe();
    const req = httpTesting.expectOne('api/nodes/deployment/disksolution');
    expect(req.request.method).toBe('GET');
  });
});
