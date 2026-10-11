import { test, expect } from '@playwright/test';

test('embedded Jalali filter limits Mehr 1403 to that month', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /سارا احمدی/ }).click();
  const frame = page.frameLocator('iframe');
  await expect(frame.getByTestId('jdf-trigger')).toContainText('بدون فیلتر');
  await frame.getByTestId('jdf-trigger').click();
  await frame.getByTestId('jdf-tab-custom').click();
  await frame.locator('select[aria-label="سال"]').selectOption('1403');
  await frame.locator('select[aria-label="ماه"]').selectOption('7');
  await frame.locator('[data-date="1403-07-01"]').click();
  await frame.locator('[data-date="1403-07-30"]').click();
  await frame.getByTestId('jdf-apply').click();
  await frame.getByRole('button', { name: 'Apply filters' }).click();
  await expect(frame.getByText('1403-07 مهر').first()).toBeVisible();
});
