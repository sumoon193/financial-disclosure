import { expect, test, type Page } from '@playwright/test'

async function login(page: Page) {
  const username=process.env.FINANCIAL_E2E_USERNAME;const password=process.env.FINANCIAL_E2E_PASSWORD
  if(!username||!password)throw new Error('BLOCKED: set FINANCIAL_E2E_USERNAME and FINANCIAL_E2E_PASSWORD')
  await page.goto('/')
  if(page.url().includes('/realms/')){await page.getByLabel(/username|用户名/i).fill(username);await page.locator('input[type="password"]').fill(password);await page.getByRole('button',{name:/sign in|登录/i}).click()}
  await expect(page.locator('.brand strong')).toHaveText('Financial Disclosure')
}

test('登录、上传申报、核验并复核持久化事实',async({page},testInfo)=>{
  const filingId=`e2e-10k-${testInfo.project.name}`
  await login(page);await page.getByRole('link',{name:'申报文件'}).click();
  const uploadResponse=page.waitForResponse(response=>response.url().includes('/api/filings/upload')&&response.request().method()==='POST')
  await page.locator('input[type=file]').setInputFiles({name:`${filingId}.html`,mimeType:'text/html',buffer:Buffer.from(`<html><body>Revenue 100.00 ${testInfo.project.name}</body></html>`)})
  expect([200,201]).toContain((await uploadResponse).status())
  await expect(page.getByText(filingId)).toBeVisible({timeout:30_000})
  await page.getByRole('link',{name:'核验与复核'}).click()
  await page.locator('[name="filingId"]').fill(filingId)
  await page.locator('[name="factName"]').fill('Revenue')
  await page.locator('[name="actualValue"]').fill('100.00')
  await page.locator('[name="expectedValue"]').fill('100.00')
  await page.locator('[name="tolerance"]').fill('0.01')
  await page.locator('[name="unit"]').fill('USD')
  await page.locator('[name="citation"]').fill(`${filingId}#revenue`)
  await page.getByTestId('create-verification').getByRole('button',{name:'创建核验'}).click()
  const runButton=page.getByRole('button').filter({hasText:filingId})
  await expect(runButton).toBeVisible({timeout:30_000})
  await runButton.click()
  await expect(page.getByText('verification-created')).toBeVisible({timeout:30_000})
  await page.locator('[name="reviewComment"]').fill('Automated review passed')
  await page.getByRole('button',{name:'通过复核'}).click()
  await expect(page.getByText('approved').first()).toBeVisible({timeout:30_000})
})

test('移动端导航和审计总览无横向溢出',async({page})=>{await login(page);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);expect(overflow).toBe(false)})
