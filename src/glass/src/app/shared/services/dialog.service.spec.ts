import { TestBed } from '@angular/core/testing';

import { MaterialModule } from '~/app/material.modules';
import { DialogService } from '~/app/shared/services/dialog.service';

describe('DialogService', () => {
  let service: DialogService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule]
    });
    service = TestBed.inject(DialogService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
