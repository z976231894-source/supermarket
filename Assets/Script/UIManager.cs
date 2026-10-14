using UnityEngine;
using UnityEngine.SceneManagement;

public class UIManager : MonoBehaviour
{
    public static UIManager Instance { get; private set; }
    [SerializeField] private GameObject MainMenu;
    [SerializeField] private GameObject screen_hud;
    [SerializeField] private GameObject screen_help;
    [SerializeField] private GameObject screen_pause;   // 设置与暂停共用这一个界面
    [SerializeField] private GameObject screen_photo;
    [SerializeField] private GameObject screen_saved;
    [SerializeField] private GameObject screen_leave;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);   // 整个 UI 物体跨场景存活
        Show(MainMenu);
    }

    // ===== 界面按钮 =====
    public void StartClick() { Show(screen_hud); }
    public void BackToMenuClick() { Show(MainMenu); }
    public void HelpClick() { Show(screen_help); }


    // ===== 内部 =====
    // 唯一的状态出口：同一时刻只保留一个界面是开的
    private void Show(GameObject screen)
    {
        SetActive(MainMenu, screen == MainMenu);
        SetActive(screen_hud, screen == screen_hud);
        SetActive(screen_pause, screen == screen_pause);
        SetActive(screen_photo, screen == screen_photo);
        SetActive(screen_saved, screen == screen_saved);
        SetActive(screen_leave, screen == screen_leave);
        SetActive(screen_help, screen == screen_help);
    }

    private static void SetActive(GameObject go, bool active)
    {
        if (go != null && go.activeSelf != active)
            go.SetActive(active);
    }
}