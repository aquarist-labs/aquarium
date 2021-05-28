import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { LocalInventoryService } from '~/app/shared/services/api/local-inventory.service';

describe('LocalInventoryService', () => {
  let service: LocalInventoryService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });

    service = TestBed.inject(LocalInventoryService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
