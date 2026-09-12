"""Run against a local Streamlit server; writes review screenshots to --output."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

p = argparse.ArgumentParser()
p.add_argument('--url', default='http://localhost:8511')
p.add_argument('--output', type=Path, required=True)
p.add_argument('--channel', default=None, help='Use chrome for an installed Google Chrome')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, channel=a.channel)
    page = browser.new_page(viewport={'width':1440,'height':1100}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(a.url)
    page.get_by_text('新发现 · 最高适应度', exact=True).wait_for(timeout=30000)
    for version in ['v0.1','v0.2','v0.3','v0.4','v0.5','v0.7']:
        page.get_by_text(version + ' ·', exact=False).first.click()
        page.locator('.chapter .eyebrow').filter(has_text=version).wait_for()
        page.wait_for_timeout(800)
        assert page.locator('[data-testid="stException"]').count() == 0
        if version != 'v0.3':
            page.get_by_role('button', name='下一步 →').click()
            page.wait_for_timeout(400)
            assert page.get_by_text('#2 ·', exact=False).count() == 1
        page.get_by_role('heading', level=1).scroll_into_view_if_needed()
        page.screenshot(path=str(a.output / f'{version}.png'), full_page=True)
        print(f'{version}: rendered and replay checked')
    page.get_by_text('理论白皮书', exact=True).click()
    page.get_by_role('heading', name='理论白皮书 / 从观察到形式化').wait_for()
    assert page.locator('[data-testid="stException"]').count() == 0
    page.get_by_text('v0.7 ·', exact=False).first.click()
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(800)
    page.get_by_role('heading', level=1).scroll_into_view_if_needed()
    page.screenshot(path=str(a.output / 'mobile.png'), full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors, errors
    browser.close()
    print('All six versions, whitepaper and mobile viewport passed.')
