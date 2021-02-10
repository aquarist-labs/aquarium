import { TestBed } from '@angular/core/testing';

import { HttpErrorInterceptorService } from '~/app/shared/services/http-error-interceptor.service';
import { SharedModule } from '~/app/shared/shared.module';

describe('HttpErrorInterceptorService', () => {
  let service: HttpErrorInterceptorService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [SharedModule]
    });
    service = TestBed.inject(HttpErrorInterceptorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
