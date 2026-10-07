package eu.svoyi.nativeapp;

import android.app.Activity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.Spinner;
import org.json.JSONObject;
import java.util.WeakHashMap;

/** One UI pass. Screen controllers retain ownership of focus, scroll and media sizing. */
public final class UiFinish256 {
    private UiFinish256() {}
    private static final WeakHashMap<Activity, Long> revisions = new WeakHashMap<>();

    public static void apply(Activity activity, JSONObject model) {
        if (activity == null || model == null) return;
        final View root = activity.findViewById(android.R.id.content);
        if (root == null) return;
        final long revision = revisions.containsKey(activity) ? revisions.get(activity) + 1 : 1;
        revisions.put(activity, revision);
        root.post(() -> {
            Long current = revisions.get(activity);
            if (current == null || current != revision || activity.isFinishing()
                    || activity.isDestroyed() || !root.isAttachedToWindow()) return;
            walk(root, activity.getResources().getDisplayMetrics().density);
        });
    }

    private static void walk(View view, float density) {
        int touch = Math.round(48 * density);
        ViewGroup.LayoutParams layout = view.getLayoutParams();
        // Fixed icon, avatar and card dimensions belong to their native screen.
        boolean flexibleHeight = layout == null || layout.height < 0;
        if (view instanceof EditText) {
            EditText input = (EditText) view;
            if (flexibleHeight) input.setMinHeight(Math.max(input.getMinHeight(), touch));
            input.setImeOptions(input.getImeOptions() | EditorInfo.IME_FLAG_NO_EXTRACT_UI);
            if ("mail-input".equals(input.getTag())) {
                input.setContentDescription("Поле нового повідомлення");
            } else if (input.getContentDescription() == null && input.getHint() != null) {
                input.setContentDescription(input.getHint());
            }
        } else if (view instanceof Button) {
            Button button = (Button) view;
            button.setAllCaps(false);
            if (flexibleHeight) button.setMinHeight(Math.max(button.getMinHeight(), touch));
        } else if (view instanceof Spinner && flexibleHeight) {
            view.setMinimumHeight(Math.max(view.getMinimumHeight(), touch));
        }
        if (view instanceof HorizontalScrollView) {
            ((HorizontalScrollView) view).setHorizontalScrollBarEnabled(false);
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) walk(group.getChildAt(i), density);
        }
    }
}
