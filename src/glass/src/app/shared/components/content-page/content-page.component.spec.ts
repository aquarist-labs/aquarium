import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CoreModule } from '~/app/core/core.module';
import { ContentPageComponent } from '~/app/shared/components/content-page/content-page.component';
import { TestingModule } from '~/app/testing.module';

describe('ContentPageComponent', () => {
  let component: ContentPageComponent;
  let fixture: ComponentFixture<ContentPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoreModule, TestingModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ContentPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
